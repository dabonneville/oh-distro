#ifndef _MapWrapper_hpp_
#define _MapWrapper_hpp_

#include <string>
#include <list>
#include <boost/shared_ptr.hpp>
#include <boost/thread/mutex.hpp>
#include <boost/thread/condition_variable.hpp>
#include <lcm/lcm-cpp.hpp>
#include <lcmtypes/drc/local_map_t.hpp>

class LocalMap;

class MapWrapper {
public:
  typedef boost::shared_ptr<const LocalMap> LocalMapConstPtr;

public:
  class UpdateListener {
  public:
    virtual void notify(MapWrapper& iWrapper) = 0;
  };

public:
  MapWrapper();
  ~MapWrapper();

  void setLcm(boost::shared_ptr<lcm::LCM>& iLcm);
  void setMapChannel(const std::string& iChannel);

  void addListener(boost::shared_ptr<UpdateListener>& iListener);
  void removeListener(boost::shared_ptr<UpdateListener>& iListener);
  void removeAllListeners();

  void operator()();
  bool start();
  bool stop();

  bool lock();
  bool unlock();

  LocalMapConstPtr getMap() const;

protected:
  void onMap(const lcm::ReceiveBuffer* iBuf,
             const std::string& iChannel,
             const drc::local_map_t* iMessage);

protected:
  boost::shared_ptr<LocalMap> mMap;
  boost::shared_ptr<LocalMap> mNewMap;
  boost::shared_ptr<lcm::LCM> mLcm;
  std::string mMapChannel;

  std::list<boost::shared_ptr<UpdateListener> > mListeners;

  lcm::Subscription* mMapSubscription;
  boost::mutex mMapMutex;
  boost::mutex mNewMapMutex;
  boost::mutex mDataReadyMutex;
  boost::condition_variable mDataReady;
  bool mNeedsUpdate;

  bool mIsRunning;

};

#endif
