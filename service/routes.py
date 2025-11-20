# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Product Store Service with UI"""

from flask import jsonify, request, abort, url_for
from service.models import Product, Category
from service.common import status
from . import app


######################################################################
# H E A L T H   C H E C K
######################################################################
@app.route("/health")
def healthcheck():
    """Let them know our heart is still beating"""
    return jsonify(status=200, message="OK"), status.HTTP_200_OK


######################################################################
# H O M E   P A G E
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


######################################################################
# U T I L I T Y   F U N C T I O N S
######################################################################
def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"Content-Type must be {content_type}")
    if request.headers["Content-Type"] != content_type:
        app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
        abort(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"Content-Type must be {content_type}")

######################################################################
# C R E A T E   A   P R O D U C T
######################################################################
@app.route("/products", methods=["POST"])
def create_products():
    """Creates a Product from posted JSON data"""
    app.logger.info("Request to create a Product")
    check_content_type("application/json")

    data = request.get_json()

    product = Product()
    product.deserialize(data)
    product.create()
    location_url = url_for("get_product", product_id=product.id, _external=True)
    return jsonify(product.serialize()), status.HTTP_201_CREATED, {"Location": location_url}

######################################################################
# R E A D   A   P R O D U C T
######################################################################
@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Retrieve a single Product by ID"""
    app.logger.info("Request to retrieve Product with id: %s", product_id)
    product = Product.find(product_id)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' was not found.")
    return jsonify(product.serialize()), status.HTTP_200_OK
    
######################################################################
# U P D A T E   A   P R O D U C T
######################################################################

@app.route("/products/<int:product_id>", methods=["PUT"])
def update_products(product_id):
    """Update a Product"""
    app.logger.info("Request to update Product with id: %s", product_id)
    check_content_type("application/json")

    product = Product.find(product_id)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' was not found.")

    product.deserialize(request.get_json())
    product.id = product_id
    product.update()
    return jsonify(product.serialize()), status.HTTP_200_OK


######################################################################
# D E L E T E   A   P R O D U C T
######################################################################
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_products(product_id):
    """Delete a Product"""
    app.logger.info("Request to delete Product with id: %s", product_id)
    product = Product.find(product_id)
    if product:
        product.delete()
    return "", status.HTTP_204_NO_CONTENT

######################################################################
# L I S T   P R O D U C T S
######################################################################


@app.route("/products", methods=["GET"])
def list_products():
    """Returns a list of Products, optionally filtered by name, category, or availability"""
    app.logger.info("Request to list Products")

    name = request.args.get("name")
    category = request.args.get("category")
    available = request.args.get("available")

    try:
        if name:
            app.logger.info("Filtering by name: %s", name)
            products = Product.find_by_name(name)
        elif category:
            app.logger.info("Filtering by category: %s", category)
            category_enum = getattr(Category, category.upper())
            products = Product.find_by_category(category_enum)
        elif available:
            app.logger.info("Filtering by availability: %s", available)
            available_value = available.lower() in ["true", "yes", "1"]
            products = Product.find_by_availability(available_value)
        else:
            app.logger.info("No filters applied. Returning all products.")
            products = Product.all()
    except AttributeError:
        abort(status.HTTP_400_BAD_REQUEST, f"Invalid category: {category}")

    results = [product.serialize() for product in products]
    app.logger.info("Returning %d products", len(results))
    return jsonify(results), status.HTTP_200_OK
