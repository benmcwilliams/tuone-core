```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "WEC Turmbau Emden"
sort location, dt_announce desc
```
