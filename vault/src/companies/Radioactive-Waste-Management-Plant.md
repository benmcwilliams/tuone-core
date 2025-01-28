```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Radioactive-Waste-Management-Plant" or company = "Radioactive Waste Management Plant")
sort location, dt_announce desc
```
