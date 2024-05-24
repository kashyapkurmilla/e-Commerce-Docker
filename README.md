# Bookstore Flask Application

This is a Flask-based web application for managing a bookstore, which allows users to view a list of products and add them to their shopping cart. The application uses MongoDB for data storage.

## Project Structure

```
e-commerce-Docker
│
├── bookstore/
│   ├── __init__.py
│   ├── db.py
│   ├── routes.py
│
├── templates/
│   ├── index.html
│   ├── view_cart.html
│
└── app.py
```

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Setting Up the Project

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/your_project.git
   cd your_project
   ```
   
2. **Build and run the application:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - The Flask application will be available at `http://localhost:8082`.
   - Mongo Express will be available at `http://localhost:8081`.
   - MinIO will be available at `http://localhost:9000`.

### Application Structure

- `app.py`: Main entry point of the Flask application.
- `bookstore/db.py`: Handles database connection and initialization.
- `bookstore/routes.py`: Contains the route handlers for the Flask application.
- `templates/index.html`: Template for the product list page.
- `templates/view_cart.html`: Template for the shopping cart page.

### Routes
- `/`: Displays the list of products.
- `/add_to_cart`: Adds a product to the user's shopping cart (POST request).
- `/view_cart`: Displays the items in the user's shopping cart.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
