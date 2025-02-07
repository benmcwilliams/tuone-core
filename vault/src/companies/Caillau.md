```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Caillau" or company = "Caillau")
sort location, dt_announce desc
```
