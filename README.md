# Forum Application

This is a forum application with a Vue.js frontend and Node.js backend.

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Create a `.env` file based on the `.env.example` file:
   ```
   cp .env.example .env
   ```

4. Reset the database (clears existing data and seeds with mock data):
   ```
   npm run reset-db
   ```

5. Start the backend server:
   ```
   npm run dev
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm run dev
   ```

## Database Management

The backend includes scripts to manage the database:

- `npm run clear-db` - Clears all data from the database
- `npm run seed` - Seeds the database with mock data
- `npm run reset-db` - Combines both (clear and seed)

## Available API Endpoints

The backend API provides the following endpoints:

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get JWT token

### Users
- `GET /api/users` - Get all users
- `GET /api/users/:id` - Get user by ID
- `GET /api/users/:id/posts` - Get posts by user ID

### Posts
- `GET /api/posts` - Get all posts with pagination
- `GET /api/posts/:id` - Get post by ID
- `POST /api/posts` - Create a new post
- `PUT /api/posts/:id` - Update post
- `DELETE /api/posts/:id` - Delete post

### Categories
- `GET /api/categories` - Get all categories
- `GET /api/categories/:id/posts` - Get posts by category

### Tags
- `GET /api/tags` - Get all tags
- `GET /api/tags/:id/posts` - Get posts by tag

### Comments
- `GET /api/posts/:id/comments` - Get comments for a post
- `POST /api/posts/:id/comments` - Add a comment to a post 