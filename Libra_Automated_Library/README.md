# Automated Library System - Frontend

A modern, responsive React frontend for an Automated Bin-Based Robotic Library System with NFC Integration.

## 🚀 Features

- **Student Dashboard**: Search books, request books, view recommendations
- **Admin Panel**: Manage requests, add books, monitor robot/bin status
- **NFC Integration**: Issue and return books via NFC interface
- **Real-time Updates**: WebSocket-ready architecture
- **Modern UI**: Beautiful gradient designs with glassmorphism effects
- **Fully Responsive**: Mobile-friendly design

## 📋 Tech Stack

- React 18 (JavaScript)
- Vite
- Tailwind CSS
- React Router DOM
- Context API for state management

## 🛠️ Installation

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

3. Build for production:
```bash
npm run build
```

## 🔐 Demo Credentials

### Student Login
- Email: `john.doe@student.edu`
- Password: `password123`

### Admin Login
- Email: `admin@library.edu`
- Password: `admin123`

## 📁 Project Structure

```
src/
├── assets/          # Images, icons, illustrations
├── components/      # Reusable UI components
├── pages/          # Page components
├── layouts/        # Layout wrappers
├── context/        # React Context providers
├── hooks/          # Custom React hooks
├── utils/          # Utility functions
├── data/           # Dummy data files
├── router/         # Routing configuration
└── styles/         # Global styles
```

## 🎨 Design Features

- Gradient backgrounds (indigo → purple → teal)
- Glassmorphism effects
- Smooth animations and transitions
- Hover effects and interactive elements
- Responsive grid layouts
- Status badges with color coding

## 📡 API Integration

The project uses mock API functions in `src/utils/api.js`. Replace these with actual API calls when connecting to the backend.

## 🔄 State Management

- **AuthContext**: User authentication state
- **BookContext**: Books, requests, recommendations
- **NotificationContext**: Toast notifications

