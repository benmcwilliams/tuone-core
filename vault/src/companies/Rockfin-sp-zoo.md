```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Rockfin sp zoo"
sort location, dt_announce desc
```
