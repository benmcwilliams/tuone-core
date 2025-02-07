```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Canal-de-Isabel-II" or company = "Canal de Isabel II")
sort location, dt_announce desc
```
