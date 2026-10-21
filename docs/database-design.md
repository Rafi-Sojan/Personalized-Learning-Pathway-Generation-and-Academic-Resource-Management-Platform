# Database design

The initial relational contract is in `database/init.sql`. Courses own concepts, concepts own resources and progress records reference both users and concepts. Roadmap items are derived data and can be regenerated from progress and dependencies.
