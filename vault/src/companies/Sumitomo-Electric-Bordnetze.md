```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Sumitomo-Electric-Bordnetze" or company = "Sumitomo Electric Bordnetze")
sort location, dt_announce desc
```
