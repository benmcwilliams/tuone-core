```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Hydrogen-Denmark" or company = "Hydrogen Denmark")
sort location, dt_announce desc
```
