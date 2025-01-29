```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "src/phases"
where location = "Voderady"
sort company, dt_announce desc
```
