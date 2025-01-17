```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Gore Street Energy Storage Fund"
sort location, dt_announce desc
```
