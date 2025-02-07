```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "GRI-Renewable-Industries" or company = "GRI Renewable Industries")
sort location, dt_announce desc
```
