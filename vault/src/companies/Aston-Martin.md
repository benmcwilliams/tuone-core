```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Aston-Martin" or company = "Aston Martin")
sort location, dt_announce desc
```
