# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Factory definitions for generating test Product instances."""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv("DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres")


class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """Initialize the database once for all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Close the database session after all tests"""
        db.session.close()

    def setUp(self):
        """Clean up the database before each test"""
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        """Remove the session after each test"""
        db.session.remove()

    def test_create_product(self):
        """It should create a Product and verify its attributes"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertIsNone(product.id)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.price, 12.50)
        self.assertTrue(product.available)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_product_to_database(self):
        """It should add a Product to the database"""
        self.assertEqual(Product.all(), [])
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, product.name)

    def test_read_product(self):
        """It should read a Product from the database"""
        product = ProductFactory()
        product.id = None
        product.create()
        found = Product.find(product.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, product.name)

    def test_update_product(self):
        """It should update a Product's description"""
        product = ProductFactory()
        product.id = None
        product.create()
        product.description = "Updated description"
        product.update()
        updated = Product.find(product.id)
        self.assertEqual(updated.description, "Updated description")

    def test_delete_product(self):
        """It should delete a Product from the database"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertEqual(len(Product.all()), 1)
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should list all Products"""
        self.assertEqual(Product.all(), [])
        for _ in range(5):
            product = ProductFactory()
            product.id = None
            product.create()
        self.assertEqual(len(Product.all()), 5)

    def test_find_by_name(self):
        """It should find Products by name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.id = None
            product.create()
        target_name = products[0].name
        expected = [p for p in products if p.name == target_name]
        found = Product.find_by_name(target_name)
        self.assertEqual(found.count(), len(expected))
        for product in found:
            self.assertEqual(product.name, target_name)

    def test_find_by_category(self):
        """It should find Products by category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.id = None
            product.create()
        target_category = products[0].category
        expected = [p for p in products if p.category == target_category]
        found = Product.find_by_category(target_category)
        self.assertEqual(found.count(), len(expected))
        for product in found:
            self.assertEqual(product.category, target_category)

    def test_find_by_availability(self):
        """It should find Products by availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.id = None
            product.create()
        target_avail = products[0].available
        expected = [p for p in products if p.available == target_avail]
        found = Product.find_by_availability(target_avail)
        self.assertEqual(found.count(), len(expected))
        for product in found:
            self.assertEqual(product.available, target_avail)

    def test_find_by_price(self):
        """It should find Products by price"""
        product = ProductFactory(price=Decimal("19.99"))
        product.id = None
        product.create()
        found = Product.find_by_price(Decimal("19.99")).all()
        self.assertGreaterEqual(len(found), 1)
        self.assertEqual(found[0].price, Decimal("19.99"))

    def test_serialize_product(self):
        """It should serialize a Product to a dictionary"""
        product = ProductFactory()
        product.id = None
        product.create()
        data = product.serialize()
        self.assertEqual(data["id"], product.id)
        self.assertEqual(data["name"], product.name)
        self.assertEqual(data["description"], product.description)
        self.assertEqual(data["price"], str(product.price))
        self.assertEqual(data["available"], product.available)
        self.assertEqual(data["category"], product.category.name)

    def test_deserialize_valid_data(self):
        """It should deserialize valid data into a Product"""
        data = {
            "name": "TestProduct",
            "description": "TestDescription",
            "price": "99.99",
            "available": True,
            "category": "FOOD"
        }
        product = Product()
        product.deserialize(data)
        self.assertEqual(product.name, "TestProduct")
        self.assertEqual(product.description, "TestDescription")
        self.assertEqual(product.price, Decimal("99.99"))
        self.assertTrue(product.available)
        self.assertEqual(product.category, Category.FOOD)

    def test_deserialize_missing_fields(self):
        """It should raise DataValidationError for missing fields"""
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize({"name": "Test"})

    def test_deserialize_invalid_types(self):
        """It should raise DataValidationError for invalid types"""
        product = Product()
        bad_data = {
            "name": "Test",
            "description": "Bad",
            "price": "10.00",
            "available": "yes",  # should be boolean
            "category": "FOOD"
        }
        with self.assertRaises(DataValidationError):
            product.deserialize(bad_data)
