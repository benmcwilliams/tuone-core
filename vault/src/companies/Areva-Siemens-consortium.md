```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Areva-Siemens-consortium" or company = "Areva Siemens consortium")
sort location, dt_announce desc
```
