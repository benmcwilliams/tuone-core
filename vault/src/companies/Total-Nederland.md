```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Total-Nederland" or company = "Total Nederland")
sort location, dt_announce desc
```
