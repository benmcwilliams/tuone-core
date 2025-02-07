```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Sur-Andévalo-Irrigation-Community" or company = "Sur Andévalo Irrigation Community")
sort location, dt_announce desc
```
