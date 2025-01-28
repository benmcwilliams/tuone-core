```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Solaris-Bus-&-Coach" or company = "Solaris Bus & Coach")
sort location, dt_announce desc
```
