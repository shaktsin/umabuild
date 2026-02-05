# Todo Tracker — Mobile App Spec for umabuild

## App Name
Todo Tracker

## Goal
A clean, production-ready TODO tracker mobile app built with Expo (React Native) that runs perfectly in Expo Web preview.

This app must look like a real shipped app — not a prototype.

---

## Core Features

1. Create a todo
   - Required: title
   - Optional: notes
2. List todos
3. Mark todo complete / incomplete
4. Edit todo
5. Delete todo (with confirmation)
6. Filter todos:
   - All
   - Active
   - Completed
7. Persist todos locally on device/browser
   - AsyncStorage on native
   - localStorage fallback for web

---

## Data Model

Each todo must have:

- id (uuid)
- title (string)
- notes (string, optional)
- completed (boolean)
- createdAt (timestamp)
- updatedAt (timestamp)

---

## UX & Design Requirements (MANDATORY)

The app MUST look production-ready by default.

### Global Layout Rules

- No UI element should touch screen edges.
- Every screen must use horizontal padding: **16–20**
- Vertical spacing between sections: **12–16**
- Touchable elements min height: **44**
- Clean typography and spacing hierarchy.

### Header (Required on every screen)

Each screen must include a top header bar:

- Left: Screen title "Todo Tracker"
- Right: “Add” button when applicable
- Header must:
  - Have padding
  - Have a subtle bottom divider
  - Be visually separated from content

### Typography

- Screen title: 22–24, bold
- Todo title: 16–18, semibold
- Body/notes: 14–16
- Muted secondary text for timestamps

### Todo Item UI

Each todo should be displayed as a card/row:

- Padding: 12–16
- Border radius: 12
- Subtle border or shadow
- Checkbox or toggle for completion
- Clear edit and delete affordances

### Empty State

When no todos exist:

- Centered message
- Friendly text like: “No todos yet. Tap Add to create one.”
- Proper spacing and alignment

### Overall Feel

The UI should feel similar to a modern productivity app:
clean, airy, and well spaced.

---

## Screens

A single main screen is acceptable if well organized.

The screen must contain:

- Header
- Filter controls (All / Active / Completed)
- Todo list
- Add button (in header or floating action)

---

## Behavior Rules

- Deleting a todo asks for confirmation
- Editing opens inline or a simple edit view
- Toggling complete updates UI instantly
- Filters update the list live

---

## Non-Goals

Do NOT include:

- Authentication
- Backend
- Push notifications
- Complex navigation
- Third-party UI libraries

Use only core React Native components.

---

## Acceptance Criteria (STRICT)

The generated app is considered correct only if:

- Every screen has a visible header
- Content has consistent padding and spacing
- The UI looks like a real app, not a wireframe
- Todos persist after refresh (web) or reload (native)
- Empty state is implemented
- Filter controls work
- Edit/Delete/Complete flows work correctly
