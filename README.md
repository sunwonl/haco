# Simple Calculator App

This is a simple calculator application designed to perform basic arithmetic operations.

## Architecture Overview

This document outlines the high-level architecture of the Calculator application, detailing its key components, data flow, and design considerations.

### 1. Key Components

The application is structured around a clear separation of concerns, ensuring modularity and maintainability. The main components are:

*   **User Interface (UI) Module**: Responsible for rendering the calculator's visual elements (buttons, display screen) and capturing user interactions. It presents the current state of the calculator to the user.

*   **Input Handler Module**: Acts as an intermediary between the UI and the Calculation Engine. It processes raw UI events (e.g., button clicks) and translates them into meaningful commands or data for the Calculation Engine. This module might handle input validation and basic parsing.

*   **Calculation Engine Module**: The core logic of the calculator. It is responsible for performing arithmetic operations based on the input received. This module maintains the calculator's internal state (current number, operator, previous number, result) and executes operations like addition, subtraction, multiplication, division, and other functions (e.g., clear, equals).

*   **State Manager (Implicit within Calculation Engine)**: Manages the current operational state of the calculator, such as the number currently being entered, the pending operation, and the accumulated result. This is often integrated directly into the Calculation Engine for simpler applications.

### 2. Data Flow

The data flow within the application follows a unidirectional pattern, ensuring predictability and easier debugging:

1.  **User Interaction**: The user interacts with the UI (e.g., clicks a number button, an operator button).
2.  **Event Dispatch**: The UI module captures this interaction and dispatches an event to the Input Handler.
3.  **Command Translation**: The Input Handler processes the UI event and translates it into a specific command or data update (e.g., `appendDigit('5')`, `setOperator('+')`, `executeOperation('=')`).
4.  **State Update**: The translated command/data is sent to the Calculation Engine. The Calculation Engine updates its internal state and performs the necessary calculations.
5.  **Result Notification**: After calculation, the Calculation Engine notifies the UI module (or a dedicated display update mechanism) about the new result or current display value.
6.  **UI Update**: The UI module receives the updated value and refreshes the display accordingly.

### 3. Design Patterns and Principles

*   **Separation of Concerns**: Each module has a distinct responsibility, reducing coupling and increasing cohesion.
*   **Event-Driven Architecture**: User interactions trigger events, which are processed by different modules.
*   **Command Pattern (Optional but Recommended)**: Operations (e.g., add, subtract, equals) can be encapsulated as command objects, allowing for easier extension, undo/redo functionality, and cleaner input handling.
*   **Observer Pattern (for UI updates)**: The UI can observe changes in the Calculation Engine's state, automatically updating the display when a new result is available.
*   **Single Responsibility Principle (SRP)**: Each class or module should have only one reason to change.

### 4. File Structure

For the backend, the core logic and tests are organized as follows:

*   `backend/calculator.py`: Contains the core calculator functions (`add`, `subtract`, `multiply`, `divide`).
*   `backend/test_calculator.py`: Contains unit tests for the functions in `calculator.py`.

### 5. Future Enhancements

*   **History Feature**: Implement a mechanism within the Calculation Engine to store a log of past operations and results.
*   **Advanced Functions**: Extend the Calculation Engine to support scientific functions (trigonometry, logarithms, etc.).
*   **Theme Customization**: Allow users to change the visual theme of the UI.
