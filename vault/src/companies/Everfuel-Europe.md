```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Everfuel-Europe" or company = "Everfuel Europe")
sort location, dt_announce desc
```
