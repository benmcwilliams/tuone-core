```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Solar-Power-Europe" or company = "Solar Power Europe")
sort location, dt_announce desc
```
