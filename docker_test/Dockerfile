# Stage 1: Builder (Unnecessary for this simple app, but included for Multi-Stage compliance and defining environment)
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    APP_USER=appuser \
    APP_HOME=/usr/src/app

# Create the application directory and set it as the working directory
WORKDIR ${APP_HOME}

# Create a non-root user and group
RUN addgroup --system ${APP_USER} && \
    adduser --system --ingroup ${APP_USER} --no-create-home ${APP_USER}

# Copy the source code (only one file)
# Since the application has NO dependencies, the build stage focuses only on setting up the source file.
# The content of main_output.py:
# import sys
# try:
#     print("Hello World!")
#     sys.exit(0)
# except Exception as e:
#     sys.exit(1)
RUN echo 'import sys\n\ntry:\n    print("Hello World!")\n    sys.exit(0)\nexcept Exception as e:\n    sys.exit(1)' > main_output.py

# Ensure the app user owns the file
RUN chown -R ${APP_USER}:${APP_USER} ${APP_HOME}


# Stage 2: Final Runtime Image (Minimal size using a highly optimized base)
FROM python:3.11-slim AS final

# Set the same variables
ENV APP_HOME=/usr/src/app \
    APP_USER=appuser

# Setup non-root user and directory
RUN addgroup --system ${APP_USER} && \
    adduser --system --ingroup ${APP_USER} --no-create-home ${APP_USER}
WORKDIR ${APP_HOME}

# Copy only the necessary source file from the builder stage
COPY --chown=${APP_USER}:${APP_USER} --from=builder ${APP_HOME}/main_output.py ./

# Drop root privileges by switching to the non-root user
USER ${APP_USER}

# Define the entrypoint to run the script
# Since the application is designed solely to output a static string and terminate,
# running it directly via CMD is the most efficient method.
CMD ["python", "main_output.py"]