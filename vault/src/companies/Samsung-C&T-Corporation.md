```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Samsung C&T Corporation"
sort location, dt_announce desc
```
