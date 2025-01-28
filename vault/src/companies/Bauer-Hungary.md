```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Bauer-Hungary" or company = "Bauer Hungary")
sort location, dt_announce desc
```
