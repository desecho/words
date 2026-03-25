Words
=====

Empty Django and Vue starter project extracted from the ``shows`` harness.

What is included
----------------
- Django 5 backend with Django REST Framework, JWT auth, and registration/reset-password flows.
- Vue 3 + Vite frontend with a minimal private route and preserved ``axios.ts`` token refresh wiring.
- Existing harness pieces such as the ``Makefile``, Docker setup, deployment manifests, helper scripts, and CI workflows.

What was removed
----------------
- The entire TV-show domain model and API surface.
- Celery and all task queue configuration.
- TMDB/OMDb/OpenAI integrations, fixtures, scheduled jobs, and related workflows.

Development
-----------
1. Copy the template env files with ``make create-env-files``.
2. Review ``env.sh``, ``env_custom.sh``, and ``env_secrets.sh``.
3. Run ``make create-venvs`` and ``make yarn-install-locked``.
4. Create the database if you want MySQL-based development, then run ``make migrate``.

Run the services with:

.. code-block:: bash

  make run
  make dev

Useful defaults
---------------
- The backend falls back to SQLite unless ``DB_ENGINE`` is set to a non-SQLite engine.
- Registration verification and password reset emails use Django's console email backend by default.
- The default frontend auth flow expects the backend at ``http://localhost:8000/``.

Deployment
----------
The repo keeps Docker, Kubernetes, and GitHub Actions scaffolding as generic templates. Update the placeholder names, image tags, domains, and secrets before using them in a real environment.
