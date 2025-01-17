```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Hyperion Energy Investment Fund SICAV P.L.C."
sort location, dt_announce desc
```
