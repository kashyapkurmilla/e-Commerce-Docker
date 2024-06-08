# Bookstore Project

This project is a web application for a bookstore where users can browse books, add them to their cart, and proceed to checkout. It includes user authentication, account management, and integration with a MongoDB database to store user information, product details, and cart items.

## Features

- **User Authentication**: Users can register, log in, and log out securely using bcrypt for password hashing.
- **Account Management**: Users can edit their account details, change passwords, and view their account information.
- **Product Catalog**: Users can browse a catalog of books available in the bookstore.
- **Shopping Cart**: Users can add books to their cart, update quantities, and remove items from the cart.
- **Checkout Process**: Users can proceed to checkout, enter shipping information, and complete their order.
- **Order History**: Users can view their past orders and order details.

## Technologies Used

- **Flask**: Python web framework used for building the backend server and handling HTTP requests.
- **MongoDB**: NoSQL database used for storing user data, product information, and cart items.
- **Docker**: Containerization tool used for deploying the application in isolated environments.
- **Stripe**: Payment processing API used for handling payments during the checkout process.
- **bcrypt**: Python library used for password hashing and authentication.
- **minio**: Object storage server used for storing book images and other media files.

## Setup and Installation

1. Clone the repository from GitHub:

```bash
git clone https://github.com/kashyapkurmilla/e-Commerce-Docker.git
```

2. Build and run the Docker containers:

```bash
docker-compose up --build
```

3. Access the application in your web browser at [http://localhost:8082](http://localhost:8082).

## Configuration

- **Environment Variables**: Configure environment variables in the `docker-compose.yml` file for MongoDB, Minio, and other services.
- **Stripe API Key**: Replace the placeholder with your actual Stripe API key in the `app.py` file.
- **Database Initialization**: Modify the `database.py` file to customize database initialization and connection settings.

## Usage

1. Register a new account or log in with existing credentials.
2. Browse the catalog and add books to your cart.
3. Proceed to checkout, enter shipping details, and complete the order.
4. View order history and account details in the user dashboard.

## Contribution

Contributions are welcome! Feel free to submit bug reports, feature requests, or pull requests to improve the project.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgements
- This project was inspired by various online bookstore platforms and Flask tutorials.
```

Feel free to customize it further to match your project's specific details and requirements!