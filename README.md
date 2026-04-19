# Flexify
![Static Badge](https://img.shields.io/badge/Hosted_on-Render_Free-purple?logo=render&logoSize=auto&link=https%3A%2F%2Fflexify-dcz4.onrender.com%2F)

Flexify is a full-stack web application designed for fitness enthusiasts who want to plan and manage their workout routines effectively. The application provides an intuitive interface for creating custom routines, adding workouts, and exploring alternatives powered by a comprehensive exercise database.

### Core Features

Flexify's functionality centers around four main capabilities:

1. **Browse Workouts** - Explore a vast collection of exercises sourced from the AscendAPI ExerciseDB, complete with descriptions, images, and demonstration videos.
2. **Create Routines** - Build personalized workout routines tailored to your fitness goals and preferences.
3. **Add Workouts to Routines** - Seamlessly add exercises to your custom routines with full control over sets, reps, and weight.
4. **View & Edit Routines** - Manage your routines with the ability to update exercises, adjust parameters, and refine your workout plans.

## Technology Stack

### Backend Framework: FastAPI

Flexify leverages **FastAPI**, a modern, high-performance Python web framework built on top of Starlette and Pydantic. FastAPI enables rapid development with automatic API documentation, built-in validation, and asynchronous request handling—making it ideal for building scalable RESTful APIs.

### External API: AscendAPI ExerciseDB

The application integrates with **[AscendAPI's ExerciseDB](https://docs.ascendapi.com/products/edb-v2/overview)**, a comprehensive exercise database that provides:

- **Extensive Exercise Library** - Access to thousands of exercises across multiple categories and muscle groups
- **Rich Media** - Each exercise includes high-quality images and instructional videos demonstrating proper form
- **Exercise Metadata** - Detailed information including target muscles, equipment needed, and difficulty levels
- **Search & Discovery** - Powerful search capabilities to find specific exercises by name, muscle group, or equipment

The AscendAPI integration allows Flexify to offer users a professional-grade exercise database without requiring manual curation. When the API key is configured, users can search for external exercises and discover workout alternatives.

**Configuration**: Add your AscendAPI credentials to the `.env` file:<br>
- `ASCEND_RAPIDAPI_KEY`="your-rapidapi-key"<br>
- `ASCEND_RAPIDAPI_HOST`="edb-with-videos-and-images-by-ascendapi.p.rapidapi.com"

## Architecture Overview

- **Models** - SQLModel classes defining database tables for users, routines, workouts, and routine-workout relationships
- **Repositories** - Data access layer handling CRUD operations on the database
- **Services** - Business logic layer enforcing rules, validation, and authorization
- **API Endpoints** - RESTful routes that accept user requests and delegate to services

## References

- AscendAPI https://ascendapi.com/
- FastAPI https://fastapi.tiangolo.com/
