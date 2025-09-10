const express = require('express');
const PON = require('../models/PON');
const Task = require('../models/Task');
const User = require('../models/User');
const { auth, authorize } = require('../middleware/auth');

const router = express.Router();

// @route   GET api/reports/dashboard
// @desc    Get dashboard statistics
// @access  Private
router.get('/dashboard', auth, async (req, res) => {
  try {
    const query = {};
    
    // Filter by role
    if (req.user.role === 'site_manager') {
      query.siteManager = req.user.id;
    } else if (req.user.role === 'project_manager') {
      query.projectManager = req.user.id;
    }

    // Get PON statistics
    const totalPONs = await PON.countDocuments(query);
    const completedPONs = await PON.countDocuments({ ...query, status: 'completed' });
    const inProgressPONs = await PON.countDocuments({ ...query, status: 'in_progress' });
    
    // Get task statistics
    const taskQuery = {};
    if (req.user.role === 'site_manager') {
      taskQuery.assignedTo = req.user.id;
    } else if (req.user.role === 'project_manager') {
      taskQuery.createdBy = req.user.id;
    }

    const totalTasks = await Task.countDocuments(taskQuery);
    const completedTasks = await Task.countDocuments({ ...taskQuery, status: 'completed' });
    const pendingTasks = await Task.countDocuments({ ...taskQuery, status: 'pending' });
    const overdueTasks = await Task.countDocuments({ 
      ...taskQuery, 
      status: { $ne: 'completed' },
      dueDate: { $lt: new Date() }
    });

    const stats = {
      pons: {
        total: totalPONs,
        completed: completedPONs,
        inProgress: inProgressPONs,
        planned: totalPONs - completedPONs - inProgressPONs
      },
      tasks: {
        total: totalTasks,
        completed: completedTasks,
        pending: pendingTasks,
        overdue: overdueTasks
      }
    };

    res.json(stats);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   GET api/reports/pons
// @desc    Get PON report data
// @access  Private
router.get('/pons', auth, async (req, res) => {
  try {
    const query = {};
    
    // Filter by role
    if (req.user.role === 'site_manager') {
      query.siteManager = req.user.id;
    } else if (req.user.role === 'project_manager') {
      query.projectManager = req.user.id;
    }

    const pons = await PON.find(query)
      .populate('projectManager', 'name email')
      .populate('siteManager', 'name email')
      .select('ponId name location status progress startDate expectedEndDate actualEndDate')
      .sort({ createdAt: -1 });

    res.json(pons);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   GET api/reports/tasks
// @desc    Get task report data
// @access  Private
router.get('/tasks', auth, async (req, res) => {
  try {
    const query = {};
    
    // Filter by role
    if (req.user.role === 'site_manager') {
      query.assignedTo = req.user.id;
    } else if (req.user.role === 'project_manager') {
      query.createdBy = req.user.id;
    }

    const tasks = await Task.find(query)
      .populate('pon', 'ponId name')
      .populate('assignedTo', 'name email')
      .populate('createdBy', 'name email')
      .select('title type status priority dueDate completedDate estimatedHours actualHours evidenceRequired evidencePhotos')
      .sort({ dueDate: 1 });

    res.json(tasks);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   GET api/reports/export/:type
// @desc    Export reports (CSV format)
// @access  Private
router.get('/export/:type', auth, async (req, res) => {
  try {
    const { type } = req.params;
    
    if (type === 'pons') {
      // Get PON data for export
      const query = {};
      if (req.user.role === 'site_manager') {
        query.siteManager = req.user.id;
      } else if (req.user.role === 'project_manager') {
        query.projectManager = req.user.id;
      }

      const pons = await PON.find(query)
        .populate('projectManager', 'name')
        .populate('siteManager', 'name');

      // Convert to CSV format
      const csvHeader = 'PON ID,Name,Location,Status,Progress,Project Manager,Site Manager,Start Date,Expected End Date,Actual End Date\n';
      const csvData = pons.map(pon => 
        `${pon.ponId},"${pon.name}","${pon.location}",${pon.status},${pon.progress}%,"${pon.projectManager?.name || ''}","${pon.siteManager?.name || ''}",${pon.startDate?.toISOString().split('T')[0] || ''},${pon.expectedEndDate?.toISOString().split('T')[0] || ''},${pon.actualEndDate?.toISOString().split('T')[0] || ''}`
      ).join('\n');

      res.setHeader('Content-Type', 'text/csv');
      res.setHeader('Content-Disposition', 'attachment; filename=pons_report.csv');
      res.send(csvHeader + csvData);
    } else {
      res.status(400).json({ message: 'Invalid export type' });
    }
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

module.exports = router;