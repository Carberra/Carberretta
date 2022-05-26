# Carberretta

This branch is for the v2 release of Carberretta.

You will need Python 3.10 or higher to run Carberretta.

## Running the bot

### Installing dependencies

```sh
# To run the bot:
pip install -r requirements.txt
python -m carberretta
```

Use CTRL+C to shut the bot down.

## Contributing

Currently, only ports of cogs from v1 are being accepted.

### Setting up

```sh
pip install -r requirements-dev.txt
```

The environment file you need is provided as `.env.example`. Rename this file to `.env`, then paste your token into the correct field.

### Checks

- Run `nox` to run various checks to make sure everything is okay. If all pipelines pass, push the changes up. If not, you'll need to make changes until they all pass.
- If you're unsure how to make a test pass, push the changes, and ask another contributor for help.
- If the `safety` check fails, raise a separate issue.

### Porting v1 cogs

When porting a cog OPEN A DRAFT PR ONCE YOU'VE MADE YOUR FIRST COMMIT. This lets me and others know that cog is already being ported. If you're unsure which cogs have been ported (or are already being ported), check the [pull requests with the type/port label](https://github.com/Carberra/Carberretta/pulls?q=is%3Apr+label%3Atype%2Fport+). Make sure to check both open AND closed PRs.

The list of cogs that are NOT to be ported:

- hub
- links
- poll
- role
- role2
- support

This is because the planned reimplementation of the cog is too different from the original, or because the cog is being removed entirely.

If you want to port the **misc** cog, it should be renamed **text**. The **meta** cog is part complete -- feel free to finish it, or have a look at the file for pointers (specifically the `/ping`, `/about` and `/stats` commands).

### Using the database

If you need to create a new table for the database, follow the naming convention set out in the data/static/build.sql file.

The database utility is now very different. Examples below:

```py
# Inserting data (from plugin)
await plugin.bot.d.db.execute("INSERT INTO ... VALUES ...", ...)

# Selecting data (from plugin)
row = await plugin.bot.d.db.try_fetch_record("SELECT user_id, points FROM experience WHERE user_id = ?", ...)
print(row.user_id)
print(row.points)
```

Datetime objects are automatically converted both ways, so fetching a field with a time in it will return a datetime object, and passing a datetime object to `execute` will insert a string timestamp.

```py
import datetime as dt

expires = await plugin.bot.d.db.try_fetch_field("SELECT expires FROM warnings WHERE user_id = ?")
isinstance(expires, dt.datetime) == True
```

Note that any method prefixed with `try_` could return `None`.
