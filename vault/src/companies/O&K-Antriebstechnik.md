```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "O&K Antriebstechnik"
sort location, dt_announce desc
```
