# Minimal, secure default. Replace with your app's build as needed.

FROM alpine:3.20 AS runtime

# Create non-root user
RUN addgroup -S app && adduser -S app -G app

WORKDIR /app

# Copy application files (replace with your build output)
# COPY --chown=app:app dist/ /app/

# Example: execute a compiled binary or start a server
# USER app
# EXPOSE 8080
# ENTRYPOINT ["/app/server"]

# The template intentionally does not run anything by default to avoid surprises.
CMD ["/bin/sh", "-c", "echo 'Replace Dockerfile with your app build & runtime.' && sleep 3600"]

