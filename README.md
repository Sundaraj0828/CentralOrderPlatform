# CentralOrderPlatform 🏢

**CentralOrderPlatform** is a centralized hub designed to unify order processing and distribution management. It acts as a middle-tier system that synchronizes data between multiple vendors and retail points, ensuring that inventory levels, order statuses, and fulfillment data are managed from a single, reliable source of truth.

---

## 🛠️ Tech Stack

* **Backend:** Python with **Flask Framework** (RESTful API architecture)
* **Database:** **MongoDB** (NoSQL for high-volume order data and flexible schemas)
* **Authentication:** JWT (JSON Web Tokens) for secure, cross-platform access
* **Configuration:** `python-dotenv` for managing environment variables and API secrets
* **Process Management:** Scalable architecture for handling concurrent order requests

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
Create a `.env` file in the project root:
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
Access the central API at `http://127.0.0.1:5000/`.

---

## 📁 Project Structure
```text
├── app/
│   ├── api/             # REST API controllers and routes
│   ├── models/          # MongoDB schemas for Orders and Inventory
│   ├── core/            # Business logic and order processing services
│   └── utils/           # Database drivers and auth helpers
├── .env                 # Environment configurations
├── app.py               # Application entry point
├── requirements.txt     # Python package list
└── README.md            # Documentation
```

---

## 🔗 Core API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/api/central/orders` | Retrieve all orders across the platform |
| **POST** | `/api/central/sync` | Manually trigger inventory synchronization |
| **PUT** | `/api/orders/<id>/status` | Update the fulfillment status of an order |
| **GET** | `/api/vendors` | List all connected suppliers |

---

## 📄 License
This project is licensed under the MIT License.

---

**Developed with ❤️ by [Sundaraj0828]**
