```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Irrigation-community" or company = "Irrigation community")
sort location, dt_announce desc
```
