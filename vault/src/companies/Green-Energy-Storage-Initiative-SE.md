```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Green Energy Storage Initiative SE"
sort location, dt_announce desc
```
