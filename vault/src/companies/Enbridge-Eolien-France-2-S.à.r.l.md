```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Enbridge Eolien France 2 S.à.r.l"
sort location, dt_announce desc
```
