```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Heerema Fabrication Group"
sort location, dt_announce desc
```
