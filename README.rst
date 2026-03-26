Words
=====

Words is a Django and Vue application for building an English/French to Russian
vocabulary list, reading saved texts, and reviewing cards with spaced
repetition.

Main Features
-------------

- Account flows for registration, email verification, login, token refresh,
  password reset, and password change.
- Word capture with Russian translation, optional English and French prompt
  values, part of speech, optional comment, and an automatically created
  per-user record.
- Text storage for English and French reading material, with highlighted tokens
  based on saved words plus automatic matches for articles, contractions, and
  number words.
- Study mode for English and French prompts with due/unseen counts and SM-2
  scheduling.
- Workbook import for bulk vocabulary loading from ``.xlsx`` files.

Stack
-----

- Backend: Django 5, Django REST Framework, Simple JWT,
  ``django-rest-registration``
- Frontend: Vue 3, Vite, TypeScript, Vuetify, Pinia, Axios
- Database: MySQL by default in ``env.sh``; SQLite is supported when
  ``DB_ENGINE=django.db.backends.sqlite3``

Backend Surface
---------------

The backend exposes:

- ``/health/`` for a simple health check
- JWT auth at ``/token/`` and ``/token/refresh/``
- registration and password flows under ``/user/``
- ``/parts-of-speech/`` and ``/words/`` for vocabulary entry
- ``/texts/`` and ``/texts/<id>/`` for saved texts
- ``/study/summary/``, ``/study/next-card/``, and ``/study/review/`` for the
  flashcard flow

Local Development
-----------------

1. Create the local env files:

   .. code-block:: bash

     make create-env-files

2. Review the env files before running the app.

   - ``env.sh`` points the backend at MySQL on ``127.0.0.1:3306`` by default.
   - If you want SQLite for local development, add
     ``export DB_ENGINE=django.db.backends.sqlite3`` to ``env_custom.sh``.
   - ``env_custom.sh.tpl`` switches email delivery to SMTP placeholders. For
     local development you probably want to set ``EMAIL_BACKEND`` back to
     ``django.core.mail.backends.console.EmailBackend`` unless you are wiring up
     SMTP.

3. Install Python and frontend dependencies:

   .. code-block:: bash

     make create-venvs
     make yarn-install-locked

4. If you are using MySQL, create the database:

   .. code-block:: bash

     make create-db

5. Run migrations and create an admin user:

   .. code-block:: bash

     make migrate
     make createsuperuser

6. Start the backend and frontend in separate terminals:

   .. code-block:: bash

     make run
     make dev

The default local URLs are:

- backend: ``http://localhost:8000/``
- frontend dev server: ``http://localhost:5173/``

Bootstrap Data
--------------

``PartOfSpeech`` rows are not seeded by migrations. Create them before using
the add-word UI or the workbook import.

The simplest path is to create a superuser and add them in Django admin. If you
prefer the shell:

.. code-block:: python

  from wordsapp.models import PartOfSpeech

  for name, abbreviation in [
      ("noun", "n"),
      ("verb", "v"),
      ("adjective", "adj"),
      ("adverb", "adv"),
      ("interjection", "int"),
      ("pronoun", "pro"),
      ("preposition", "pre"),
      ("conjunction", "c"),
      ("determiner", "d"),
  ]:
      PartOfSpeech.objects.get_or_create(
          name=name,
          defaults={"abbreviation": abbreviation},
      )

Importing Words From Excel
--------------------------

The management command imports a workbook into ``Word`` and ``Record`` rows:

.. code-block:: bash

  make manage import_words arguments="--file /absolute/path/to/words.xlsx"

Import details:

- The default file path is ``<repo>/words.xlsx``.
- The workbook headers must be exactly:
  ``frequency``, ``word``, ``pos``, ``word_ru``, ``word_fr``.
- Supported ``pos`` abbreviations are ``v``, ``n``, ``r``, ``j``, ``u``,
  ``pro``, ``pre``, ``c``, and ``d``.
- The command currently imports into ``User`` id ``1``. Make sure that user
  exists before running the import.
- Matching ``PartOfSpeech`` names must already exist:
  ``verb``, ``noun``, ``adverb``, ``adjective``, ``interjection``,
  ``pronoun``, ``preposition``, ``conjunction``, ``determiner``.
- Imports are transactional and reject duplicate frequencies plus duplicate
  ``(word, part_of_speech)`` pairs.

Study Flow
----------

- Prompts are shown as English or French words with the part-of-speech
  abbreviation, plus an optional comment.
- Answers are always Russian.
- New eligible cards can be ignored once.
- Reviews use SM-2 scheduling with ``correct`` and ``incorrect`` grades.
- Due cards are shown before unseen cards, and unseen cards are prioritized by
  word frequency when available.

Texts
-----

- Saved texts are scoped per user and can be deleted from the UI.
- Text processing lemmatizes saved words to find matches in the text.
- English articles, contractions, and number words are highlighted even without
  saved vocabulary.
- French article forms, contractions, and number words are also highlighted
  automatically.
- The frontend includes a subtitle-cleanup helper for pasted subtitle files.

Testing
-------

Useful commands during development:

.. code-block:: bash

  make pytest
  make mypy
  make test

Deployment Notes
----------------

The repository still includes Docker, Kubernetes, and deployment helper
scripts. They are wired for this project, but they still need real environment
values, image publishing, and secret management before production use.
