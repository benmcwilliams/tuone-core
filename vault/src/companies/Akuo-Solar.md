```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Akuo-Solar" or company = "Akuo Solar")
sort location, dt_announce desc
```
