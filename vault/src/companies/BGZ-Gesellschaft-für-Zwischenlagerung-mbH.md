```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "BGZ Gesellschaft für Zwischenlagerung mbH"
sort location, dt_announce desc
```
