/**
 * Database seeding script.
 * Run with: node scripts/seed.js
 */

require('dotenv').config();
const { MongoClient } = require('mongodb');
const { seedDatabase } = require('../database/seeders/DatabaseSeeder');

// Get database connection string from environment variables or use default
const DB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/forum';

async function main() {
  const client = new MongoClient(DB_URI);
  
  try {
    console.log('Connecting to database...');
    await client.connect();
    console.log('Connected successfully to database');
    
    const db = client.db();
    
    // Run the seeder
    await seedDatabase(db);
    
    console.log('Seeding completed! You can now start your application.');
  } catch (error) {
    console.error('Error during seeding:', error);
    process.exit(1);
  } finally {
    // Close the database connection
    await client.close();
  }
}

// Run the main function
main().catch(console.error); 