## Project Overview

Clara is an open-source, AI-powered personal assistant designed to manage everyday work and life through simple conversation. The project aims to create a comprehensive personal operating system that connects with users personally and helps them accomplish tasks across multiple platforms and services. Clara acts as a conversational interface that understands user needs and executes actions across integrated services, making daily task management seamless and efficient.

## Project Vision

Clara is being built as an open-source personal assistant that connects with users personally and helps them get things done across daily tasks. With your permission, Clara can connect to the services you use every day, creating a unified experience where users can manage their entire digital life through natural conversation. The vision extends beyond simple task completion to becoming a trusted digital companion that understands user context, preferences, and needs over time.

## Core Architecture

### Platform Support

The project plans to support multiple platforms to ensure Clara is accessible wherever users need assistance. **Android** is the first planned platform, providing mobile accessibility for the majority of users. Coming soon are **Windows desktop**, **iOS**, and **macOS** applications, each designed to leverage platform-specific capabilities while maintaining a consistent Clara experience across all devices. This multi-platform approach ensures users can interact with Clara whether they're at their desk, on the go, or using their preferred device ecosystem.

### Skills System

Clara is being developed with a growing set of skills that represent the core capabilities of the assistant. These modular skills include **Email assistance** for managing inboxes and composing messages, **Presentation creation** for building professional slides, **Research assistance** for gathering and synthesizing information, **Coding assistance** for programming tasks, and **Task and reminder management** for keeping users organized. Each skill is designed to be independently developed and maintained, allowing for rapid expansion of Clara's capabilities as the project grows.

### Integrations

With user permission, Clara will be able to work with various services to execute tasks on behalf of users. Key integrations include **Gmail** for email management, **Google Calendar** for scheduling and event management, **Google Drive** for document storage and collaboration, **Google Tasks** for task tracking, and many more as the project expands. This integration framework follows a permission-based model where Clara only accesses services when explicitly authorized by the user, ensuring privacy and security remain paramount.

### Authentication & Authorization

The project uses Google OAuth 2.0 for authentication with support for multiple client types to accommodate different platform requirements. **Web applications** utilize client secret-based authentication for server-side security, **Desktop applications** implement public client flows with localhost callback for native desktop experiences, and **Mobile applications** use public client flows with custom URI schemes for mobile platforms. This comprehensive authentication strategy ensures secure, seamless login experiences across all supported platforms while maintaining Google's security standards.

### API Layer

The backend API layer serves as the communication bridge between frontend clients and Clara's core services. It handles **Authentication routes** for user login and token management, **Token management** for maintaining secure sessions, **Service integrations** for communicating with external services, and **Request routing** for directing user requests to the appropriate skill handlers. The API is designed to be RESTful and scalable, supporting multiple concurrent users while maintaining performance and reliability.

### Connections System

The connections system provides modular handlers for different Google services, abstracting the complexity of API interactions. These handlers include implementations for **Google Calendar** for event management, **Google Drive** for file operations, **Gmail** for email operations, and other Google services as needed. Each connection handler follows a standardized interface, making it easy to add support for new services while maintaining consistency across the system.

### Configuration

Centralized configuration management is implemented using environment variables with sensible defaults to simplify deployment and development. The configuration system handles **OAuth credentials** for authentication, **JWT settings** for secure token generation, **API keys** for external service access, and **Service endpoints** for API communication. This approach allows developers to easily switch between development, testing, and production environments without code changes.

## Technology Stack

### Backend

The backend is built using **Python 3.14+** as the primary programming language, chosen for its extensive ecosystem of libraries and frameworks. **Google API Client libraries** provide robust integration with Google services, **JWT** (JSON Web Tokens) are used for secure session management and authentication, and **OAuth 2.0** provides industry-standard authorization flows. This combination of technologies ensures a secure, scalable, and maintainable backend system.

### Dependencies

Core dependencies include **google-api-python-client** for comprehensive Google service integration, **google-auth** for authentication handling, **google-auth-httplib2** for HTTP transport, **google-auth-oauthlib** for OAuth flows, **python-dotenv** for environment variable management, and **setuptools** for package management and distribution. These carefully selected dependencies provide the foundation for Clara's functionality while minimizing unnecessary bloat.

## Key Components

### Authentication Module (`clara/auth/`)

The authentication module handles Google OAuth 2.0 flows for multiple platforms with distinct implementations. **Web application authentication** uses client secrets for server-side security, **Desktop application authentication** implements public client flows with localhost callback, and **Mobile application authentication** uses custom URI schemes for platform integration. Additional functionality includes **Token exchange and refresh** for maintaining active sessions and **User information retrieval** for profile management, ensuring a comprehensive authentication solution.

### Settings Management (`clara/conf/`)

Centralized configuration with environment variable support manages all system settings. The settings include **OAuth credentials per platform** for secure service access, **JWT configuration** for token generation, **Service scopes** defining access permissions, **Redirect URIs** for OAuth flows, and **Validation of required settings** to prevent configuration errors. This centralized approach simplifies configuration management and ensures consistent behavior across environments.

### API Module (`clara/api/`)

The API module defines endpoints and route handling for the backend services. Key endpoints include **Authentication endpoints** for user login and session management, **Token management endpoints** for refreshing and validating tokens, and **Route configuration** for mapping requests to handlers. The API follows RESTful design principles and is structured to be both developer-friendly and secure.

### Connections Module (`clara/connections/`)

Service-specific connection handlers provide standardized interfaces for external service integration. The module includes implementations for **Google Calendar integration** for event operations, **Google Drive integration** for file management, **Gmail integration** for email operations, a **Connection registry** for service management, and **Base connection classes** that define standardized interfaces. This modular architecture allows for easy addition of new service integrations.

### Skills Module (`clara/skills/`)

Modular skill implementations are organized in the skills module, each representing a distinct capability. Each skill includes **Email assistant skills** for email management, **Workflow definitions** that define the skill's operational logic, **Skill configuration (YAML)** for metadata and settings, and **Prompt management** for defining interaction templates. This structure enables independent development and maintenance of each skill.

## Development Status

Clara is currently in active development with features, integrations, and supported platforms continuing to evolve as the project grows. The modular architecture allows for parallel development of different components, enabling the community to contribute to various aspects of the project independently. Regular updates and improvements are expected as the project moves toward stable releases.

## Contribution Guidelines

The project welcomes contributions from the community in various forms. Contributors can add **New skills** to expand Clara's capabilities, implement **Feature enhancements** to improve existing functionality, submit **Bug fixes** to address issues, improve **Documentation** to help other developers, add **Platform support** for new operating systems, and create **Integration with new services** to expand Clara's reach. The open-source nature of the project encourages community involvement and collective improvement.

## License

BSD 3-Clause License - Copyright (c) 2026, Aryan Vishwakarma. This license allows for both commercial and non-commercial use, modification, and distribution of the software, provided that proper attribution is maintained and the copyright notice is preserved. The permissive nature of the BSD license encourages widespread adoption and contribution to the project.