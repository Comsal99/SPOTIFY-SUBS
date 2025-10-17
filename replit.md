# Subscription Cost-Sharing Manager

## Overview

This is a Streamlit-based web application for managing shared subscription costs among multiple members. The application allows tracking monthly payments across different years, calculating member payment statistics, and maintaining a complete payment history. Users can manage subscription slots, set pricing, and monitor who has paid for each month of the year.

## User Preferences

Preferred communication style: Simple, everyday language.

## View Modes

The application now supports two distinct views:

1. **Member View (Read-Only)**:
   - Default view for regular members
   - Can view member lists, payment summaries, dashboard statistics, payment history
   - Can download backups
   - Cannot add/remove members, edit payments, or restore backups
   - No access to payment editing tab

2. **Admin View (Full Access)**:
   - Protected by password authentication (default: "admin123", configurable via ADMIN_PASSWORD environment variable)
   - Full access to all features including:
     - Add/remove members
     - Edit payment status (individual and bulk)
     - Modify subscription settings
     - Manage years (add new years, copy members)
     - Restore from backups
   - Additional "Payments" tab for payment tracking and editing

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit for the web interface
- **Design Pattern**: Single-page application with sidebar navigation
- **State Management**: Streamlit session state for year selection and UI state persistence
- **Caching Strategy**: Resource caching (`@st.cache_resource`) for the DataManager singleton to avoid repeated instantiation

### Backend Architecture
- **Core Components**:
  - `DataManager`: Handles all data persistence operations with year-based file organization
  - `utils`: Provides utility functions for currency formatting, payment calculations, and validation
  - `app.py`: Main application entry point and UI rendering logic

- **Data Model**:
  - Year-based data structure with members list, payment tracking dictionary, payment history log, and configurable settings
  - Payment tracking uses nested dictionaries: `{member_name: {month: boolean}}`
  - Payment history maintains an audit trail with timestamps, actions, and status changes
  - Settings include total subscription price and maximum available slots

### Data Storage
- **File-based JSON Storage**: Each year's data stored in separate JSON files (`subscription_data_{year}.json`)
- **Directory Structure**: Data files organized in a `data/` directory
- **Auto-initialization**: Creates default data structure if files don't exist
- **Data Schema**:
  ```
  {
    year: integer,
    members: array of strings,
    payments: object mapping members to monthly payment status,
    payment_history: array of payment change events,
    settings: {total_price, max_slots},
    created_at: ISO timestamp,
    updated_at: ISO timestamp
  }
  ```

### Key Design Decisions

**File-based Storage over Database**
- **Problem**: Need persistent storage for subscription payment data
- **Solution**: JSON files organized by year in the filesystem
- **Rationale**: Simplifies deployment, no database setup required, easy to backup and version control
- **Trade-offs**: Limited scalability and concurrent access, but suitable for small team usage

**Year-based Data Partitioning**
- **Problem**: Managing multi-year subscription data efficiently
- **Solution**: Separate JSON file per year with year selection in UI
- **Rationale**: Prevents data files from growing too large, allows archiving old years, improves load performance
- **Benefits**: Clear data organization, faster file operations, easier data management

**Payment Status Tracking**
- **Problem**: Track which members paid for which months
- **Solution**: Boolean dictionary per member with month keys
- **Alternatives**: Could use date ranges or individual payment records
- **Chosen Approach**: Simple true/false per month provides clear status and easy UI rendering

**Audit Trail via Payment History**
- **Problem**: Need to track when payment statuses change
- **Solution**: Append-only payment_history array with timestamps and state changes
- **Rationale**: Provides accountability and allows future analytics or dispute resolution

## External Dependencies

### Python Libraries
- **streamlit**: Web application framework for the user interface
- **pandas**: Data manipulation and analysis (for potential reporting features)
- **json**: Built-in library for data serialization/deserialization
- **datetime**: Built-in library for timestamp management

### File System
- Local file system for JSON data storage in `data/` directory
- No external database or cloud storage services currently integrated

### Future Integration Points
- The architecture supports adding external storage (cloud storage, databases) by extending the DataManager class
- Payment processing integrations could be added via the payment_history tracking mechanism
- Export functionality could leverage pandas for CSV/Excel generation