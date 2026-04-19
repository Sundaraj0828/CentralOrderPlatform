# CentralOrderPlatform 🏢

**CentralOrderPlatform** is a centralized hub designed to unify order processing and distribution management across multiple nodes. It acts as a middle-tier system that synchronizes data between vendors and retail points, ensuring that inventory levels, order statuses, and fulfillment data are managed from a single, reliable source of truth.

---

## 🛠️ Tech Stack

* **Backend:** Python with **Flask Framework** (RESTful API architecture)
* **Database:** **MongoDB** (NoSQL for high-volume order data and flexible schemas)
* **Authentication:** JWT (JSON Web Tokens) for secure, cross-platform access
* **Configuration:** `python-dotenv` for managing environment variables and API secrets
* **Process Management:** Scalable architecture for handling concurrent order requests from various retailers

---

## ✨ Key Features

* **Unified Order Dashboard:** A single interface to view and manage orders from various sources.
* **Centralized Inventory:** Real-time tracking of stock levels across the entire network.
* **Vendor Management:** Tools to integrate and monitor multiple suppliers.
* **Order Fulfillment Workflow:** Automated status updates from "Pending" to "Dispatched" and "Delivered."
* **Data Analytics:** Insightful reporting on order volumes, peak times, and vendor performance.

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.10+
* MongoDB installed and running locally or via MongoDB Atlas

### 2. Installation
Clone the repository to your local machine:
```bash
git clone https://github.com/Sundaraj0828/CentralOrderPlatform.git
cd CentralOrderPlatform
```

### 3. Configuration
Create a `.env` file in the project root to store your credentials:
```env
MONGO_URI=mongodb://localhost:27017/central_order_db
JWT_SECRET_KEY=your_central_secure_key
FLASK_APP=app.py
FLASK_ENV=development
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
flask run
```

---

## 📁 Project Structure

```text
CentralOrderPlatform/
├── app/
│   ├── api/             # REST API controllers and routes
│   │   ├── auth.py      # Authentication logic
│   │   ├── orders.py    # Order management endpoints
│   │   └── inventory.py # Inventory sync endpoints
│   ├── models/          # MongoDB document schemas
│   │   ├── user.py      # User and Role models
│   │   ├── order.py     # Order and Item models
│   │   └── vendor.py    # Vendor and Supplier models
│   ├── core/            # Business logic and services
│   └── utils/           # Database drivers and auth helpers
├── .env                 # Environment configurations (Hidden)
├── app.py               # Application entry point
├── requirements.txt     # Python package list
└── README.md            # Documentation
```

---

## 📊 Entity Relationship (ER) Diagram

The system uses a document-oriented approach in MongoDB. Below is the logical relationship between the core entities:



* **Users:** Manages credentials and roles (Admin, Retailer, Vendor).
* **Vendors:** Contains supplier details and linked product catalogs.
* **Orders:** Bridges Retailers and Vendors, containing multiple line items and status tracking.
* **Inventory:** Tracks stock levels across different warehouse locations.

---

## 🔗 Core API Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/auth/login` | Obtain access token | No |
| **GET** | `/api/central/orders` | Retrieve all platform orders | Yes |
| **POST** | `/api/central/sync` | Trigger inventory synchronization | Yes |
| **PUT** | `/api/orders/<id>/status`| Update fulfillment status | Yes |

---

## 📄 License
This project is licensed under the MIT License.

---

**Developed with ❤️ by [Sundaraj0828]**
