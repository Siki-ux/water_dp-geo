For changes in the model

1. Modify the tables / view etc. as you like

2. Write a flyway migration in `flyway/migrations/public` that
    runs for each existing schema and make the transition from
    the existing state to the new desired state.
    In the end the resulting data model modified by flyway must be
    identical to the data model defined in step 1.