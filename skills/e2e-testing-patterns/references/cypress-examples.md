## Cypress Patterns

### Setup and Configuration

```typescript
// cypress.config.ts
import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    baseUrl: "http://localhost:3000",
    viewportWidth: 1280,
    viewportHeight: 720,
    video: false,
    screenshotOnRunFailure: true,
    defaultCommandTimeout: 10000,
    requestTimeout: 10000,
    setupNodeEvents(on, config) {
      // Implement node event listeners
    },
  },
});
```

### Pattern 1: Custom Commands

```typescript
// cypress/support/commands.ts
declare global {
  namespace Cypress {
    interface Chainable {
      login(email: string, password: string): Chainable<void>;
      createUser(userData: UserData): Chainable<User>;
      dataCy(value: string): Chainable<JQuery<HTMLElement>>;
    }
  }
}

Cypress.Commands.add("login", (email: string, password: string) => {
  cy.visit("/login");
  cy.get('[data-testid="email"]').type(email);
  cy.get('[data-testid="password"]').type(password);
  cy.get('[data-testid="login-button"]').click();
  cy.url().should("include", "/dashboard");
});

Cypress.Commands.add("createUser", (userData: UserData) => {
  return cy.request("POST", "/api/users", userData).its("body");
});

Cypress.Commands.add("dataCy", (value: string) => {
  return cy.get(`[data-cy="${value}"]`);
});

// Usage
cy.login("user@example.com", "password");
cy.dataCy("submit-button").click();
```

### Pattern 2: Cypress Intercept

```typescript
// Mock API calls
cy.intercept("GET", "/api/users", {
  statusCode: 200,
  body: [
    { id: 1, name: "John" },
    { id: 2, name: "Jane" },
  ],
}).as("getUsers");

cy.visit("/users");
cy.wait("@getUsers");
cy.get('[data-testid="user-list"]').children().should("have.length", 2);

// Modify responses
cy.intercept("GET", "/api/users", (req) => {
  req.reply((res) => {
    // Modify response
    res.body.users = res.body.users.slice(0, 5);
    res.send();
  });
});

// Simulate slow network
cy.intercept("GET", "/api/data", (req) => {
  req.reply((res) => {
    res.delay(3000); // 3 second delay
    res.send();
  });
});
```

