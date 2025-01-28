```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Hamburg-Green-Hydrogen-Hub" or company = "Hamburg Green Hydrogen Hub")
sort location, dt_announce desc
```
