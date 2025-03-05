/**
 * Database clearing script.
 * Run with: node scripts/clear-db.js
 * 
 * This script clears all data from the database before seeding.
 */

require('dotenv').config();
const { MongoClient } = require('mongodb');
const { clearDatabase } = require('../database/seeders/DatabaseSeeder');

// Get database connection string from environment variables or use default
const DB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/forum';

async function main() {
  const client = new MongoClient(DB_URI);
  
  try {
    console.log('Connecting to database...');
    await client.connect();
    console.log('Connected successfully to database');
    
    const db = client.db();
    
    // Clear the database
    await clearDatabase(db);
    
    console.log('Database cleared successfully! You can now run the seeder script to populate it with fresh data.');
  } catch (error) {
    console.error('Error during database clearing:', error);
    process.exit(1);
  } finally {
    // Close the database connection
    await client.close();
  }
}

// Run the main function
main().catch(console.error); 