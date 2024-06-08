### Step-by-Step Instructions

1. **Copy `products.json` into the MongoDB container**:

   Use the `docker cp` command to copy the file into the MongoDB container (`e-commerce-docker-mongo-1`).

   ```bash
   docker cp /mnt/data/products.json e-commerce-docker-mongo-1:/data/products.json
   ```

2. **Import the JSON file into MongoDB**:

   Access the MongoDB container:

   ```bash
   docker exec -it e-commerce-docker-mongo-1 bash
   ```

   Inside the MongoDB container, use the `mongoimport` tool to import the data into the `bookstore` database and the `products` collection:

   ```bash
    mongoimport --username <username> --password <password> --authenticationDatabase admin --db bookstore --collection products --file /data/products.json --jsonArray
   ```

#### Using Mongo Express

1. Open a web browser and go to `http://localhost:8081`. This is the port where Mongo Express should be running, as specified in your `docker-compose.yaml`.
    
2. Once in Mongo Express, navigate to the `bookstore` database and then to the `products` collection to see the imported documents.
